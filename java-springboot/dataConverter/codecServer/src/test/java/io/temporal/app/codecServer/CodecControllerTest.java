/*
 * MIT License
 *
 * Copyright (c) 2024 temporal.io
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package io.temporal.app.codecServer;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.google.protobuf.ByteString;
import io.temporal.api.common.v1.Payload;
import io.temporal.common.converter.EncodingKeys;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/** Unit tests for the CodecController REST endpoints. */
@WebMvcTest(CodecController.class)
class CodecControllerTest {

  @Autowired private MockMvc mockMvc;

  @Test
  void testHealthEndpoint() throws Exception {
    mockMvc
        .perform(get("/health"))
        .andExpect(status().isOk())
        .andExpect(content().contentType(MediaType.APPLICATION_JSON))
        .andExpect(jsonPath("$.status").value("OK"))
        .andExpect(jsonPath("$.message").value("Codec server is running"));
  }

  @Test
  void testEncodeEndpoint() throws Exception {
    // Create a simple payload for testing
    Payload testPayload =
        Payload.newBuilder()
            .putMetadata(
                EncodingKeys.METADATA_ENCODING_KEY,
                ByteString.copyFrom("json/plain", StandardCharsets.UTF_8))
            .setData(ByteString.copyFrom("{\"test\":\"data\"}", StandardCharsets.UTF_8))
            .build();

    String requestJson =
        String.format(
            "{\"payloads\":[{\"metadata\":{\"%s\":\"%s\"},\"data\":\"%s\"}]}",
            EncodingKeys.METADATA_ENCODING_KEY,
            "json/plain",
            java.util.Base64.getEncoder().encodeToString("{\"test\":\"data\"}".getBytes()));

    mockMvc
        .perform(post("/encode").contentType(MediaType.APPLICATION_JSON).content(requestJson))
        .andExpect(status().isOk())
        .andExpect(content().contentType(MediaType.APPLICATION_JSON))
        .andExpect(jsonPath("$.payloads").isArray());
  }

  @Test
  void testDecodeEndpoint() throws Exception {
    // Create an encrypted payload for testing decode
    String requestJson =
        "{\"payloads\":[{\"metadata\":{\"encoding\":\"binary/encrypted\"},\"data\":\"dGVzdA==\"}]}";

    mockMvc
        .perform(post("/decode").contentType(MediaType.APPLICATION_JSON).content(requestJson))
        .andExpect(status().isOk())
        .andExpect(content().contentType(MediaType.APPLICATION_JSON))
        .andExpect(jsonPath("$.payloads").isArray());
  }

  @Test
  void testEncodeWithInvalidPayload() throws Exception {
    String invalidJson = "{\"payloads\":[{\"invalid\":\"structure\"}]}";

    mockMvc
        .perform(post("/encode").contentType(MediaType.APPLICATION_JSON).content(invalidJson))
        .andExpect(status().isBadRequest());
  }

  @Test
  void testDecodeWithInvalidPayload() throws Exception {
    String invalidJson = "{\"payloads\":[{\"invalid\":\"structure\"}]}";

    mockMvc
        .perform(post("/decode").contentType(MediaType.APPLICATION_JSON).content(invalidJson))
        .andExpect(status().isBadRequest());
  }
}
