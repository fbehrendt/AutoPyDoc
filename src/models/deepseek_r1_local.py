from gpt4all import GPT4All

from .model_strategy import DocstringModelStrategy


class LocalDeepseekR1Strategy(DocstringModelStrategy):
    def __init__(self, device="cuda"):
        super().__init__()

        self.device = device

        model_name = "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"

        self.logger.info(
            "Using GPT4All model [%s] on device [%s]", model_name, self.device
        )
        self.gpt_model = GPT4All(model_name=model_name, device=self.device)

    def generate_docstring(
        self, code_generation_input: str, existing_docstring: str
    ) -> str:
        try:
            with self.gpt_model.chat_session():
                prompt = self.build_prompt(existing_docstring, code_generation_input)

                self.logger.debug("Using prompt [%s]", prompt)
                self.logger.info("Starting docstring generation")

                def generation_callback(token_id, token):
                    print(token, end="")

                    return True

                generated_text = self.gpt_model.generate(
                    prompt=prompt,
                    temp=0.6,
                    max_tokens=1000,
                    callback=generation_callback,
                )

                self.logger.info("Finished docstring generation [%s]", generated_text)

                return generated_text
        except Exception as e:
            self.logger.exception(
                "An error occurred during docstring generation", exc_info=e
            )
            raise e

    def build_prompt(self, existing_docstring: str, code_content: str) -> str:
        # Followed Prompt Guidelines:
        # - https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt
        # - https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B#usage-recommendations

        return f"""
You are an AI documentation assistant, and your task is to evaluate if an existing function docstring correctly descibes the given code of the function.
The purpose of the documentation is to help developers and beginners understand the function and specific usage of the code.

The existing docstring is as follows:
'''
{existing_docstring}
'''

The content of the code is as follows:
'''
{code_content}
'''

If the existing docstring matches the code, please output `TRUE`, otherwise, please output `false`.
Please reason step by step, and put your final answer within {{
    "analysis": "your analysis goes here",
    "matches": true or false
}}
<think>
"""
