import unittest

from datasets import load_dataset

from fabricator.prompts import BasePrompt
from fabricator.dataset_transformations.question_answering import *
from fabricator.dataset_transformations.text_classification import *
from fabricator.dataset_transformations.token_classification import *


class TestTransformationsTextClassification(unittest.TestCase):
    """Testcase for ClassLabelPrompt"""

    def setUp(self) -> None:
        self.dataset = load_dataset("trec", split="train")

    def test_label_ids_to_textual_label(self):
        """Test transformation output only"""
        dataset, label_options = convert_label_ids_to_texts(self.dataset, "coarse_label", return_label_options=True)
        self.assertEqual(len(label_options), 6)
        self.assertEqual(set(label_options), set(self.dataset.features["coarse_label"].names))
        self.assertEqual(type(dataset[0]["coarse_label"]), str)
        self.assertNotEqual(type(dataset[0]["coarse_label"]), int)
        self.assertIn(dataset[0]["coarse_label"], label_options)

    def test_formatting_with_textual_labels(self):
        """Test formatting with textual labels"""
        dataset, label_options = convert_label_ids_to_texts(self.dataset, "coarse_label", return_label_options=True)
        fewshot_examples = dataset.select([1, 2, 3])
        prompt = BasePrompt(
            task_description="Annotate the question into following categories: {}.",
            generate_data_for_column="coarse_label",
            fewshot_example_columns="text",
            label_options=label_options,
        )
        raw_prompt = prompt.get_prompt_text(label_options, fewshot_examples)
        self.assertIn("text: What films featured the character Popeye Doyle ?\ncoarse_label: ENTY", raw_prompt)
        for label in label_options:
            self.assertIn(label, raw_prompt)

    def test_expanded_textual_labels(self):
        """Test formatting with expanded textual labels"""
        extended_mapping = {
            "DESC": "Description",
            "ENTY": "Entity",
            "ABBR": "Abbreviation",
            "HUM": "Human",
            "NUM": "Number",
            "LOC": "Location",
        }
        dataset, label_options = convert_label_ids_to_texts(
            self.dataset, "coarse_label", expanded_label_mapping=extended_mapping, return_label_options=True
        )
        self.assertIn("Location", label_options)
        self.assertNotIn("LOC", label_options)
        fewshot_examples = dataset.select([1, 2, 3])
        prompt = BasePrompt(
            task_description="Annotate the question into following categories: {}.",
            generate_data_for_column="coarse_label",
            fewshot_example_columns="text",
            label_options=label_options,
        )
        raw_prompt = prompt.get_prompt_text(label_options, fewshot_examples)
        self.assertIn("text: What films featured the character Popeye Doyle ?\ncoarse_label: Entity", raw_prompt)
        self.assertNotIn("ENTY", raw_prompt)
        for label in label_options:
            self.assertIn(label, raw_prompt)

    def test_textual_labels_to_label_ids(self):
        """Test conversion back to label ids"""
        dataset, label_options = convert_label_ids_to_texts(self.dataset, "coarse_label", return_label_options=True)
        self.assertIn(dataset[0]["coarse_label"], label_options)
        dataset = dataset.class_encode_column("coarse_label")
        self.assertIn(dataset[0]["coarse_label"], range(len(label_options)))

    def test_false_inputs_raises_error(self):
        """Test that false inputs raise errors"""
        with self.assertRaises(AttributeError):
            dataset, label_options = convert_label_ids_to_texts("coarse_label", "dataset")


class TestTransformationsTokenClassification(unittest.TestCase):
    """Testcase for TokenLabelTransformations"""

    def setUp(self) -> None:
        self.dataset = load_dataset("conll2003", split="train").select(range(150))

    def test_bio_tokens_to_spans(self):
        """Test transformation output only (BIO to spans)"""
        dataset, label_options = convert_token_labels_to_spans(
            self.dataset, "tokens", "ner_tags", return_label_options=True
        )
        self.assertEqual(len(label_options), 4)
        self.assertEqual(type(dataset[0]["ner_tags"]), str)
        self.assertNotEqual(type(dataset[0]["ner_tags"]), int)
        spans = list(dataset[0]["ner_tags"].split("\n"))
        for span in spans:
            self.assertTrue(any(label in span for label in label_options))

    def test_formatting_with_span_labels(self):
        """Test formatting with span labels"""
        dataset, label_options = convert_token_labels_to_spans(
            dataset=self.dataset,
            token_column="tokens",
            label_column="ner_tags",
            return_label_options=True
        )
        fewshot_examples = dataset.select([1, 2, 3])
        prompt = BasePrompt(
            task_description="Annotate each of the following tokens with the following labels: {}.",
            generate_data_for_column="ner_tags",
            fewshot_example_columns="tokens",
            label_options=label_options,
        )
        raw_prompt = prompt.get_prompt_text(label_options, fewshot_examples)
        self.assertIn("Peter Blackburn is PER entity.", raw_prompt)
        self.assertIn("BRUSSELS is LOC entity.", raw_prompt)
        for label in label_options:
            self.assertIn(label, raw_prompt)

    def test_expanded_textual_labels(self):
        """Test formatting with expanded textual labels"""
        expanded_label_mapping = {
            0: "O",
            1: "B-person",
            2: "I-person",
            3: "B-location",
            4: "I-location",
            5: "B-organization",
            6: "I-organization",
            7: "B-miscellaneous",
            8: "I-miscellaneous",
        }

        dataset, label_options = convert_token_labels_to_spans(
            dataset=self.dataset,
            token_column="tokens",
            label_column="ner_tags",
            expanded_label_mapping=expanded_label_mapping,
            return_label_options=True
        )
        fewshot_examples = dataset.select([1, 2, 3])
        prompt = BasePrompt(
            task_description="Annotate each of the following tokens with the following labels: {}.",
            generate_data_for_column="ner_tags",
            fewshot_example_columns="tokens",
            label_options=label_options,
        )
        raw_prompt = prompt.get_prompt_text(label_options, fewshot_examples)
        self.assertIn("Peter Blackburn is person entity.", raw_prompt)
        self.assertNotIn("PER", raw_prompt)
        for label in label_options:
            self.assertIn(label, raw_prompt)

    def test_textual_labels_to_label_ids(self):
        """Test conversion back to label ids on token-level"""
        dataset, label_options = convert_token_labels_to_spans(
            dataset=self.dataset,
            token_column="tokens",
            label_column="ner_tags",
            return_label_options=True
        )
        id2label = dict(enumerate(self.dataset.features["ner_tags"].feature.names))
        self.assertEqual(dataset[0]["ner_tags"], "EU is ORG entity.\nGerman is MISC entity.\nBritish is MISC entity.")
        dataset = dataset.select(range(10))
        dataset = convert_spans_to_token_labels(
            dataset=dataset,
            token_column="tokens",
            label_column="ner_tags",
            id2label=id2label
        )
        for label in dataset[0]["ner_tags"]:
            self.assertIn(label, id2label.keys())

    def test_false_inputs_raises_error(self):
        """Test that false inputs raise errors"""
        with self.assertRaises(AttributeError):
            dataset, label_options = convert_token_labels_to_spans(
                "ner_tags", "tokens", {1: "a", 2: "b", 3: "c"}
            )

        with self.assertRaises(AttributeError):
            dataset, label_options = convert_token_labels_to_spans(
                {1: "a", 2: "b", 3: "c"}, "tokens", "ner_tags"
            )


class TestTransformationsQuestionAnswering(unittest.TestCase):
    """Testcase for QA Transformations"""

    def setUp(self) -> None:
        self.dataset = load_dataset("squad_v2", split="train")

    def test_squad_preprocessing(self):
        """Test transformation from squad fromat into flat structure"""
        self.assertEqual(type(self.dataset[0]["answers"]), dict)
        dataset = preprocess_squad_format(self.dataset.select(range(30)))
        self.assertEqual(type(dataset[0]["answers"]), str)
        with self.assertRaises(KeyError):
            x = dataset[0]["answer_start"]

    def test_squad_postprocessing(self):
        """Test transformation flat structure into squad format"""
        dataset = preprocess_squad_format(self.dataset.select(range(50)))
        dataset = postprocess_squad_format(dataset)
        self.assertEqual(type(dataset[0]["answers"]), dict)
        self.assertIn("answer_start", dataset[0]["answers"])
