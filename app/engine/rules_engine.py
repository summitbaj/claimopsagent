import yaml
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Trigger(BaseModel):
    field: str
    contains: str

class Action(BaseModel):
    target_entity: str
    update_field: str
    value: str
    criteria: Optional[str] = "ALL"

class Rule(BaseModel):
    id: str
    description: str
    trigger: Trigger
    action: Action

class RulesEngine:
    def __init__(self, config_path: str = "config/rules.yaml"):
        self.rules = self._load_rules(config_path)

    def _load_rules(self, path: str) -> List[Rule]:
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return [Rule(**r) for r in data.get("rules", [])]
        except Exception as e:
            print(f"Error loading rules: {e}")
            return []

    def evaluate(self, claim: Dict[str, Any]) -> List[Rule]:
        """Returns a list of rules that match the claim."""
        matches = []
        for rule in self.rules:
            val = claim.get(rule.trigger.field, "")
            if val and rule.trigger.contains in str(val):
                matches.append(rule)
        return matches
