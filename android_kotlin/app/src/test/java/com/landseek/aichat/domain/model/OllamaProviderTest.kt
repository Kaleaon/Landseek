package com.landseek.aichat.domain.model

import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test
import retrofit2.Call
import retrofit2.Response

class OllamaProviderTest {

    @Test
    fun `complete returns content when api call is successful`() = runBlocking {
        // Arrange
        val mockApi = mockk<OllamaApi>()
        val mockCall = mockk<Call<OllamaChatResponse>>()
        val provider = OllamaProvider(model = "gemma", api = mockApi)
        val messages = listOf(RLMMessage(role = "user", content = "Hello"))

        val expectedResponse = OllamaChatResponse(
            model = "gemma",
            createdAt = "2024-01-01T00:00:00Z",
            message = OllamaMessage(role = "assistant", content = "Hi there!"),
            done = true
        )

        every { mockApi.chat(any()) } returns mockCall
        every { mockCall.execute() } returns Response.success(expectedResponse)

        // Act
        val result = provider.complete(messages, 0.7f)

        // Assert
        assertEquals("Hi there!", result)
        verify {
            mockApi.chat(withArg {
                assertEquals("gemma", it.model)
                assertEquals(1, it.messages.size)
                assertEquals("user", it.messages[0].role)
                assertEquals("Hello", it.messages[0].content)
                assertEquals(0.7f, it.options?.temperature)
            })
        }
    }
}
