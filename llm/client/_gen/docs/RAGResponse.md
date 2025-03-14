# RAGResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**answer** | **str** |  | 
**sources** | **List[str]** |  | 
**usage** | **object** |  | 

## Example

```python
from llm_service.models.rag_response import RAGResponse

# TODO update the JSON string below
json = "{}"
# create an instance of RAGResponse from a JSON string
rag_response_instance = RAGResponse.from_json(json)
# print the JSON string representation of the object
print(RAGResponse.to_json())

# convert the object into a dict
rag_response_dict = rag_response_instance.to_dict()
# create an instance of RAGResponse from a dict
rag_response_from_dict = RAGResponse.from_dict(rag_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


