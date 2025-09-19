from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model


__all__ = ['load_chat_model']

def load_chat_model(fully_specified_model_name:str, **kwargs) -> BaseChatModel:
    """Ouput the model. Input is in form provider/model"""

    if "/" in fully_specified_model_name:
        provider, model = fully_specified_model_name.split("/", maxsplit=1)

    else:
        provider = ""
        model = fully_specified_model_name

    return init_chat_model(model=model, model_provider=provider , **kwargs)
    


