import logging
import random
from abc import abstractmethod
from typing import List, Optional

from langchain.chains import LLMChain
from langchain.llms import BaseLLM

from ai_dataset_generator.prompt_templates import BasePrompt
from ai_dataset_generator.task_templates import BaseDataPoint, TextDataPoint

logger = logging.getLogger(__name__)


class DatasetGenerator:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    @abstractmethod
    def postprocess_prompt(self, pred: str) -> BaseDataPoint:
        pass

    def generate(
        self,
        support_examples: List[BaseDataPoint],
        prompt_template: BasePrompt,
        unlabeled_examples: Optional[List[BaseDataPoint]] = None,
        support_examples_per_prompt: int = 2,
        num_samples_to_generate: int = 10,
        max_prompt_calls: int = 10,
    ) -> List[BaseDataPoint]:
        if not all(hasattr(obj, attr) for obj in support_examples for attr in prompt_template.support_set_variables):
            raise RuntimeError("Not all samples have the required attributes for the generation prompt template.")

        generated_samples: List[BaseDataPoint] = []

        if unlabeled_examples is None:
            input_examples = iter(max(max_prompt_calls, num_samples_to_generate) * [TextDataPoint(text="")])
        else:
            input_examples = iter(unlabeled_examples)

        for prompt_call_idx, input_example in enumerate(input_examples, start=1):
            # TODO @All we need ideally one example per class, don't do it purely
            #  randomly, at least for text classification, but I guess also for NER etc
            #  it would be more efficient to have some logic to select the examples
            #  (while of course keeping as much randomness as possible)
            sampled_support_examples = random.sample(support_examples, support_examples_per_prompt)
            prompt = prompt_template.get_prompt(sampled_support_examples)
            chain = LLMChain(llm=self.llm, prompt=prompt)
            formatted_input = prompt_template.format_input(input_example)
            logger.debug(f"Formatted input: {formatted_input}")
            pred = chain.run(formatted_input)
            generated_samples.append(prompt_template.add_annotation_to_input(input_example, pred))

            if prompt_call_idx >= max_prompt_calls:
                logger.info(f"Reached maximum number of prompt calls ({max_prompt_calls}).")
                break

            if len(generated_samples) >= num_samples_to_generate:
                logger.info(f"Generated {num_samples_to_generate} samples.")
                break

        return generated_samples
