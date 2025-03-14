# RAGRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** |  | 
**context_window** | **int** |  | [optional] [default to 2000]

## Example

```python
from llm_service.models.rag_request import RAGRequest

# TODO update the JSON string below
json = "{}"
# create an instance of RAGRequest from a JSON string
rag_request_instance = RAGRequest.from_json(json)
# print the JSON string representation of the object
print(RAGRequest.to_json())

# convert the object into a dict
rag_request_dict = rag_request_instance.to_dict()
# create an instance of RAGRequest from a dict
rag_request_from_dict = RAGRequest.from_dict(rag_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


