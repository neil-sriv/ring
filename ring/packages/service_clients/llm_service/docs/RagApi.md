# llm_service.RagApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**query_rag_rag_query_post**](RagApi.md#query_rag_rag_query_post) | **POST** /rag/query | Query Rag


# **query_rag_rag_query_post**
> RAGResponse query_rag_rag_query_post(rag_request)

Query Rag

Stub endpoint for RAG query

### Example

* Api Key Authentication (APIKeyHeader):

```python
import llm_service
from llm_service.models.rag_request import RAGRequest
from llm_service.models.rag_response import RAGResponse
from llm_service.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = llm_service.Configuration(
    host = "/api/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with llm_service.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = llm_service.RagApi(api_client)
    rag_request = llm_service.RAGRequest() # RAGRequest | 

    try:
        # Query Rag
        api_response = api_instance.query_rag_rag_query_post(rag_request)
        print("The response of RagApi->query_rag_rag_query_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RagApi->query_rag_rag_query_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **rag_request** | [**RAGRequest**](RAGRequest.md)|  | 

### Return type

[**RAGResponse**](RAGResponse.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

