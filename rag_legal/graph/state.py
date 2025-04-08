from dataclasses import dataclass, field
from typing import Dict, List
from langgraph.graph import MessagesState

@dataclass(kw_only=True)
class State(MessagesState):
    """The state of your graph / agent."""
    create_summary: bool = field(
        default=False,
        metadata={"description": "Indica si se debe crear un resumen de la conversación."}
        )
    
    summary: str = field(
        default="",
        metadata={"description": "Resumen de la conversación anterior."}
        )
    
    query: List[str] = field(
        default_factory=list,
        metadata={"description": "Consulta del usuario, puede ser re-escrita."}
        )
    
    context: str = field(
        default="",
        metadata={"description": "Contexto de la consulta."}
        )
    
    token_cost: float = field(
        default=0,
        metadata={"description": "Costo de los tokens."}
        )
    
    is_relevant: bool = field(
        default=False,
        metadata={"description": "Indica si la consulta es relevante."}
        )

    # @classmethod
    # def update_token_info(cls, state: dict, new_token_info: Dict[str, float]) -> dict:
    #     """Actualiza el campo 'token_info' de un dict de estado."""
    #     current_token_info = state.get("token_info", {})
    #     for key, value in new_token_info.items():
    #         if key in current_token_info:
    #             current_token_info[key] += value
    #         else:
    #             current_token_info[key] = value
    #     state["token_info"] = current_token_info
    #     return state


__all__ = ["State"]