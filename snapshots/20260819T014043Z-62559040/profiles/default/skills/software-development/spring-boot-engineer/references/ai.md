# Spring AI — Chat Models, Embeddings, Vector Stores, RAG & Function Calling

> Reference for: Spring Boot Engineer
> Load when: Integrating LLM chat models, embeddings, vector stores, RAG pipelines, or function calling with Spring AI

## Dependencies

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
</dependency>

<!-- Vector store -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-pgvector-spring-boot-starter</artifactId>
</dependency>

<!-- Or Chroma -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-chroma-store-spring-boot-starter</artifactId>
</dependency>
```

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: gpt-4o
          temperature: 0.7
          max-tokens: 2000
      embedding:
        options:
          model: text-embedding-3-small
    vectorstore:
      pgvector:
        index-type: hnsw
        distance-type: cosine
        dimensions: 1536
```

## Chat Client

### ChatClient (Fluent API)

```java
@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatClient.Builder chatClientBuilder;

    private ChatClient chatClient;

    @PostConstruct
    void init() {
        chatClient = chatClientBuilder
            .defaultSystem("You are a helpful assistant for an e-commerce platform.")
            .build();
    }

    public String ask(String question) {
        return chatClient.prompt()
            .user(question)
            .call()
            .content();
    }

    public String askWithContext(String question, String context) {
        return chatClient.prompt()
            .system("Answer based only on the provided context. If the context doesn't contain the answer, say 'I don't know'.")
            .user(u -> u.text(question + "\n\nContext:\n" + context))
            .call()
            .content();
    }
}
```

### Streaming responses

```java
public Flux<String> streamChat(String question) {
    return chatClient.prompt()
        .user(question)
        .stream()
        .content();
}
```

### Structured output (response as POJO)

```java
public record SentimentAnalysis(String sentiment, double confidence, String summary) {}

public SentimentAnalysis analyzeSentiment(String text) {
    return chatClient.prompt()
        .system("Analyze the sentiment of the following text. Return positive, negative, or neutral with a confidence score.")
        .user(text)
        .call()
        .entity(SentimentAnalysis.class);
}
```

### Chat with conversation history

```java
@Service
@RequiredArgsConstructor
public class ConversationService {

    private final ChatClient chatClient;

    public String chat(String sessionId, String userMessage) {
        // Build a message list with history
        List<Message> messages = new ArrayList<>();

        // Load previous messages for this session
        messages.addAll(loadHistory(sessionId));

        // Add new user message
        messages.add(new UserMessage(userMessage));

        // Send to model
        String response = chatClient.prompt()
            .messages(messages)
            .call()
            .content();

        // Persist the exchange
        saveExchange(sessionId, userMessage, response);

        return response;
    }
}
```

## Embeddings

```java
@Service
@RequiredArgsConstructor
public class EmbeddingService {

    private final EmbeddingModel embeddingModel;

    public float[] embed(String text) {
        EmbeddingResponse response = embeddingModel.embedForResponse(List.of(text));
        return response.getResults().get(0).getOutput();
    }

    public List<float[]> embedBatch(List<String> texts) {
        EmbeddingResponse response = embeddingModel.embedForResponse(texts);
        return response.getResults().stream()
            .map(Embedding::getOutput)
            .toList();
    }
}
```

## Vector Store

### Storing documents

```java
@Service
@RequiredArgsConstructor
public class DocumentIngestionService {

    private final VectorStore vectorStore;
    private final EmbeddingModel embeddingModel;

    public void ingestDocument(String content, Map<String, Object> metadata) {
        Document doc = new Document(content, metadata);
        vectorStore.add(List.of(doc));
    }

    public void ingestFromFile(Path filePath) throws IOException {
        String content = Files.readString(filePath);
        ingestDocument(content, Map.of(
            "source", filePath.getFileName().toString(),
            "ingestedAt", Instant.now().toString()
        ));
    }
}
```

### Similarity search

```java
@Service
@RequiredArgsConstructor
public class SimilaritySearchService {

    private final VectorStore vectorStore;

    public List<Document> search(String query, int topK) {
        return vectorStore.similaritySearch(
            SearchRequest.query(query)
                .withTopK(topK)
                .withSimilarityThreshold(0.7)
        );
    }

    public List<Document> searchWithFilter(String query, String category) {
        return vectorStore.similaritySearch(
            SearchRequest.query(query)
                .withTopK(5)
                .withFilterExpression("category == '" + category + "'")
        );
    }
}
```

## RAG (Retrieval-Augmented Generation)

### Basic RAG pipeline

```java
@Service
@RequiredArgsConstructor
public class RagService {

    private final ChatClient chatClient;
    private final VectorStore vectorStore;

    public String answerWithContext(String question) {
        // 1. Retrieve relevant documents
        List<Document> docs = vectorStore.similaritySearch(
            SearchRequest.query(question).withTopK(5).withSimilarityThreshold(0.7)
        );

        // 2. Build context from documents
        String context = docs.stream()
            .map(Document::getText)
            .collect(Collectors.joining("\n\n---\n\n"));

        // 3. Generate answer using context
        return chatClient.prompt()
            .system("""
                You are a knowledgeable assistant. Answer the user's question based
                ONLY on the provided context. If the context doesn't contain relevant
                information, say "I don't have enough information to answer that."
                """)
            .user(u -> u.text("""
                Question: %s

                Context:
                %s
                """.formatted(question, context)))
            .call()
            .content();
    }
}
```

### RAG with document chunking

```java
@Service
@RequiredArgsConstructor
public class DocumentChunkingService {

    private final VectorStore vectorStore;

    public void ingestLargeDocument(String fullText, int chunkSize, int overlap) {
        // Split into overlapping chunks
        List<String> chunks = splitIntoChunks(fullText, chunkSize, overlap);

        List<Document> documents = chunks.stream()
            .map(chunk -> new Document(chunk, Map.of(
                "source", "large-doc",
                "chunkedAt", Instant.now().toString(),
                "chunkSize", chunkSize
            )))
            .toList();

        vectorStore.add(documents);
    }

    private List<String> splitIntoChunks(String text, int size, int overlap) {
        List<String> chunks = new ArrayList<>();
        int start = 0;
        while (start < text.length()) {
            int end = Math.min(start + size, text.length());
            chunks.add(text.substring(start, end));
            start += (size - overlap);
        }
        return chunks;
    }
}
```

## Function Calling (Tools)

### Define a function

```java
@Bean
public Function<OrderStatusRequest, OrderStatusResponse> checkOrderStatus(OrderRepository orderRepository) {
    return request -> {
        Order order = orderRepository.findById(request.orderId())
            .orElseThrow(() -> new ResourceNotFoundException("Order not found"));
        return new OrderStatusResponse(order.getId(), order.getStatus().name(), order.getTotal());
    };
}

public record OrderStatusRequest(Long orderId) {}
public record OrderStatusResponse(Long orderId, String status, BigDecimal total) {}
```

### Use function in chat

```java
public String askWithTools(String question) {
    return chatClient.prompt()
        .user(question)
        .functions("checkOrderStatus")   // bean name
        .call()
        .content();
}
```

### Dynamic function registration

```java
public String askWithDynamicTool(String question) {
    return chatClient.prompt()
        .user(question)
        .functions(
            FunctionCallback.builder()
                .function("searchProducts", searchProductsFunction())
                .description("Search products by name or category")
                .inputType(SearchRequest.class)
                .build()
        )
        .call()
        .content();
}
```

## Multi-Model Configuration

```yaml
spring:
  ai:
    openai:
      chat:
        options:
          model: gpt-4o
          temperature: 0.3
    # Can configure multiple providers
    # ollama:
    #   chat:
    #     options:
    #       model: llama3
    #   embedding:
    #     options:
    #       model: nomic-embed-text
    anthropic:
      chat:
        options:
          model: claude-sonnet-4-20250514
```

```java
@Service
public class MultiModelService {

    private final ChatClient openaiClient;
    private final ChatClient anthropicClient;

    public MultiModelService(
            @Qualifier("openAiChatClient") ChatClient.Builder openaiBuilder,
            @Qualifier("anthropicChatClient") ChatClient.Builder anthropicBuilder) {
        this.openaiClient = openaiBuilder.build();
        this.anthropicClient = anthropicBuilder.build();
    }

    public String compare(String question) {
        String openaiAnswer = openaiClient.prompt().user(question).call().content();
        String anthropicAnswer = anthropicClient.prompt().user(question).call().content();
        return "OpenAI: " + openaiAnswer + "\n\nAnthropic: " + anthropicAnswer;
    }
}
```

## Testing

```java
@SpringBootTest
class RagServiceTest {

    @MockBean
    private VectorStore vectorStore;

    @MockBean
    private ChatClient.Builder chatClientBuilder;

    @Test
    void shouldAnswerWithContext() {
        // Given
        Document doc = new Document("Orders can be cancelled within 24 hours of placement.");
        when(vectorStore.similaritySearch(any()))
            .thenReturn(List.of(doc));

        ChatClient mockClient = mock(ChatClient.class);
        when(chatClientBuilder.build()).thenReturn(mockClient);
        // ... configure mock response

        // When
        String answer = ragService.answerWithContext("Can I cancel my order?");

        // Then
        assertThat(answer).contains("24 hours");
    }
}
```

## Quick Reference

| Concern | Primary API | Notes |
|---|---|---|
| Chat | `ChatClient.prompt().user().call()` | Fluent API |
| Streaming | `.stream().content()` | Returns `Flux<String>` |
| Structured output | `.call().entity(Class)` | Maps response to POJO |
| Embeddings | `EmbeddingModel.embedForResponse()` | Batch embedding supported |
| Vector store | `VectorStore.add()` / `.similaritySearch()` | PgVector, Chroma, Redis |
| RAG | Retrieve → context → chat | Combine search + chat |
| Function calling | `.functions("beanName")` | Spring bean as LLM tool |
| Dynamic tool | `FunctionCallback.builder()` | Runtime tool registration |
| Multi-model | Qualifier on `ChatClient.Builder` | Route to different providers |
| Chunking | Split text with overlap | 500–1000 chars, 10–20% overlap |

## Common Pitfalls

1. **No similarity threshold.** Without `withSimilarityThreshold()`, the vector store returns low-relevance results that pollute the RAG context. Set a threshold (0.7 is a reasonable starting point).

2. **Chunking too small or too large.** Chunks under 200 characters lose semantic context; chunks over 2000 characters dilute relevance. Aim for 500–1000 characters with 10–20% overlap.

3. **Not handling streaming errors.** `Flux<String>` from `.stream()` can fail mid-stream. Use `.onErrorResume()` or `.onErrorMap()` to handle connection or rate-limit errors gracefully.

4. **Embedding model mismatch.** If you switch embedding models (e.g., from `text-embedding-3-small` to `text-embedding-3-large`), existing vectors in the store are incompatible. Re-embed all documents.

5. **No metadata filtering.** Storing all documents without metadata makes filtered retrieval impossible. Always attach metadata (source, date, category, tenant) when ingesting.

6. **Exposing function calling without auth.** LLM-triggered functions execute with application privileges. Ensure functions are read-only or add explicit authorization checks inside the function body.

7. **Token limit overflow in RAG.** Stuffing too many retrieved documents into the prompt exceeds the model's context window. Limit context size or use a map-reduce summarization approach for large contexts.

8. **Not testing function calling.** Function calling behavior is non-deterministic — the model may or may not decide to call a function. Test both paths: function called and function not called.

9. **Hardcoding model names in code.** Model names change frequently. Configure via `application.yml` or environment variables so deployments can switch models without code changes.

10. **No rate limiting on chat endpoints.** LLM calls are expensive and slow. Add rate limiting (e.g., Bucket4j or Redis-based) to any endpoint that triggers a chat completion.