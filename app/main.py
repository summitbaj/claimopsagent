import argparse
import sys
import json
from app.core.telemetry import setup_telemetry
from app.chains.prediction import PredictionChain
from app.chains.guidance import GuidanceChain
from app.chains.correction import CorrectionChain
from app.chains.analytics import AnalyticsChain

def main():
    setup_telemetry()
    
    parser = argparse.ArgumentParser(description="Intelligent Claims Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Predict
    predict_parser = subparsers.add_parser("predict", help="Predict claim outcome")
    predict_parser.add_argument("claim_id", type=str, help="Claim ID to analyze")

    # Guide
    guide_parser = subparsers.add_parser("guide", help="Get billing guidance")
    guide_parser.add_argument("query", type=str, help="Question about billing SOPs")

    # Correct
    correct_parser = subparsers.add_parser("correct", help="Apply auto-corrections")
    correct_parser.add_argument("claim_id", type=str, help="Claim ID to process")

    # Analyze
    subparsers.add_parser("analyze", help="Generate analytics report")

    args = parser.parse_args()

    if args.command == "predict":
        print(f"🔍 Analyzing Claim {args.claim_id}...")
        chain = PredictionChain()
        result = chain.predict(args.claim_id)
        print(json.dumps(result, indent=2))

    elif args.command == "guide":
        print(f"📘 Searching SOPs for: {args.query}...")
        chain = GuidanceChain()
        result = chain.get_guidance(args.query)
        print("\n--- Guidance ---\n")
        print(result)

    elif args.command == "correct":
        print(f"🛠️  Evaluating Corrections for Claim {args.claim_id}...")
        chain = CorrectionChain()
        result = chain.process_claim(args.claim_id)
        print(json.dumps(result, indent=2))

    elif args.command == "analyze":
        print("📊 Generating Analytics Report...")
        chain = AnalyticsChain()
        result = chain.generate_report()
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
