from typing import Dict, Any, List
from pydantic import BaseModel

class ChartSpec(BaseModel):
    chart_type: str
    title: str
    x_axis_label: str
    y_axis_label: str
    data: Dict[str, Any]
    summary: str

class InfographicGenerator:
    @staticmethod
    def generate_bar_chart(title: str, data: Dict[str, float], x_label: str, y_label: str, summary: str) -> Dict:
        return ChartSpec(
            chart_type="bar",
            title=title,
            x_axis_label=x_label,
            y_axis_label=y_label,
            data=data,
            summary=summary
        ).model_dump()

    @staticmethod
    def generate_pie_chart(title: str, data: Dict[str, float], summary: str) -> Dict:
        return ChartSpec(
            chart_type="pie",
            title=title,
            x_axis_label="Category",
            y_axis_label="Share",
            data=data,
            summary=summary
        ).model_dump()
