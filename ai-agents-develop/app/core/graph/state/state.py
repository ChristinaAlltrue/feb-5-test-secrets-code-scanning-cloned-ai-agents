from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_ai.messages import ModelMessage

from app.core.agents.compliance_agent.models import ComplianceInput


class State(BaseModel):
    """
    State class to manage the mutable execution state of a graph.
    It holds only the data that changes during graph execution.

    Public attributes:
        output (list): List to store the output of each node.
        node_ind (int): The index of the current node being executed
        final_result (dict): The final result of the graph execution.
    """

    output: list = Field(default_factory=list)  # output of each node
    generated_files: list = Field(default_factory=list)  # generated files of each node
    node_ind: int = 0  # index of the current node
    agent_messages: List[ModelMessage] = Field(
        default_factory=list
    )  # agent message history for pause/resume

    data: Optional[dict] = Field(None)  # TODO: connect the input output of node from UI

    def manual_init(self, num_nodes: int):
        """Initialize the state with the number of nodes"""
        if not self.output or len(self.output) != num_nodes:
            self.output = [{} for _ in range(num_nodes)]
            self.generated_files = [[] for _ in range(num_nodes)]

    def store_output(self, output: dict):
        """Stores the output of the current node"""
        self.output[self.node_ind] = output

    def store_generated_files(self, generated_files: list):
        """Stores the generated files of the current node"""
        self.generated_files[self.node_ind] = generated_files

    def transform_to_compliance_input(self) -> List[ComplianceInput]:
        """
        transform the output for the compliance judgement container.
        """
        return [ComplianceInput(**i) for i in self.output]

    def get_generated_files(self) -> List[Path]:
        """Get the generated files from the state"""
        result = []
        for node in self.generated_files:
            for file in node:
                result.append(Path(file))
        return result

    def get_uploaded_files(self) -> list:
        """Get the uploaded files from the state"""
        result = []
        for node in self.output:
            if "execution_files" in node:
                result.extend(node["execution_files"])
        return result

    def store_agent_messages(self, messages: List[ModelMessage]) -> None:
        """Store agent messages for pause/resume functionality"""
        self.agent_messages.extend(messages)

    def get_agent_messages(self) -> List[ModelMessage]:
        """Get stored agent messages for pause/resume functionality"""
        return self.agent_messages
