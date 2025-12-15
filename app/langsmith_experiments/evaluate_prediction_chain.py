import os
from dotenv import load_dotenv

# Load environment variables (including LANGSMITH_API_KEY)
load_dotenv()

from langsmith import Client, wrappers
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
from openai import OpenAI
from app.chains.prediction import PredictionChain
from app.core.config import settings
import asyncio

# 1. Initialize LangSmith client
client = Client()

DATASET_NAME = "predictionchain-eval"

# Try to get the dataset if it exists, otherwise create it
try:
    dataset = client.read_dataset(dataset_name=DATASET_NAME)
except ValueError as e:
    # Only create if the error is "not found"
    if "not found" in str(e).lower():
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Evaluation dataset for PredictionChain"
        )
    else:
        raise

# 3. Add examples (inputs/expected outputs) if needed
examples = [
    {
        "inputs": {"claim_id": "41fcffdf-65a3-f011-bbd3-00224802c180"},
        "outputs": {"prediction": "PASS"},  # Expected output for evaluation
    },
    # Add more examples as needed
]
client.create_examples(dataset_id=dataset.id, examples=examples)

# 4. Define the target function to evaluate
def target(inputs: dict) -> dict:
    chain = PredictionChain(token=None)
    # Run the async predict method synchronously
    result = asyncio.run(chain.predict(inputs["claim_id"]))
    return result if isinstance(result, dict) else {"prediction": result}

# 5. Define an LLM-as-a-judge evaluator for correctness
def correctness_evaluator(inputs, outputs, reference_outputs):
    evaluator = create_llm_as_judge(
        prompt=CORRECTNESS_PROMPT,
        model=settings.OPENAI_MODEL,
        feedback_key="correctness",
    )
    eval_result = evaluator(
        inputs=inputs, outputs=outputs, reference_outputs=reference_outputs
    )
    return eval_result

# 6. Run the evaluation
experiment_results = client.evaluate(
    target,
    data=dataset.id,
    evaluators=[correctness_evaluator],
    experiment_prefix="predictionchain-experiment",
    max_concurrency=2,
)

print("Experiment completed. Results:", experiment_results)