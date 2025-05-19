# llm_service.EmbeddingsApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**embed_embeddings_embed_post**](EmbeddingsApi.md#embed_embeddings_embed_post) | **POST** /embeddings/embed | Embed
[**test_completion_embeddings_test_post**](EmbeddingsApi.md#test_completion_embeddings_test_post) | **POST** /embeddings/test | Test Completion


# **embed_embeddings_embed_post**
> EmbeddingResponse embed_embeddings_embed_post(embedding_request)

Embed

Stub endpoint for text completion generation

### Example

* Api Key Authentication (APIKeyHeader):

```python
import llm_service
from llm_service.models.embedding_request import EmbeddingRequest
from llm_service.models.embedding_response import EmbeddingResponse
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
    api_instance = llm_service.EmbeddingsApi(api_client)
    embedding_request = llm_service.EmbeddingRequest() # EmbeddingRequest | 

    try:
        # Embed
        api_response = api_instance.embed_embeddings_embed_post(embedding_request)
        print("The response of EmbeddingsApi->embed_embeddings_embed_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EmbeddingsApi->embed_embeddings_embed_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **embedding_request** | [**EmbeddingRequest**](EmbeddingRequest.md)|  | 

### Return type

[**EmbeddingResponse**](EmbeddingResponse.md)

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

# **test_completion_embeddings_test_post**
> EmbeddingResponse test_completion_embeddings_test_post()

Test Completion

Test endpoint that returns an embedding for a test text

### Example

* Api Key Authentication (APIKeyHeader):

```python
import llm_service
from llm_service.models.embedding_response import EmbeddingResponse
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
    api_instance = llm_service.EmbeddingsApi(api_client)

    try:
        # Test Completion
        api_response = api_instance.test_completion_embeddings_test_post()
        print("The response of EmbeddingsApi->test_completion_embeddings_test_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EmbeddingsApi->test_completion_embeddings_test_post: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**EmbeddingResponse**](EmbeddingResponse.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

