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

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.util.JsonFormat;
import io.temporal.api.common.v1.Payload;
import java.io.IOException;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Configuration class for the Codec Server that handles JSON serialization/deserialization of
 * Temporal Payload objects using Protocol Buffers JSON format.
 */
@Configuration
public class CodecServerConfig {

  /**
   * Configures Jackson ObjectMapper to handle Temporal Payload serialization/deserialization.
   *
   * @return Configured ObjectMapper with custom Payload serializers
   */
  @Bean
  @Primary
  public ObjectMapper objectMapper() {
    ObjectMapper mapper = new ObjectMapper();
    SimpleModule module = new SimpleModule();

    // Add custom serializer and deserializer for Payload objects
    module.addSerializer(Payload.class, new PayloadSerializer());
    module.addDeserializer(Payload.class, new PayloadDeserializer());

    mapper.registerModule(module);
    return mapper;
  }

  /**
   * Configures CORS settings for the codec server to allow cross-origin requests.
   *
   * @return WebMvcConfigurer with CORS configuration
   */
  @Bean
  public WebMvcConfigurer corsConfigurer() {
    return new WebMvcConfigurer() {
      @Override
      public void addCorsMappings(CorsRegistry registry) {
        registry
            .addMapping("/**")
            .allowedOrigins("*")
            .allowedMethods("POST", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(false);
      }
    };
  }

  /**
   * Custom Jackson serializer for Temporal Payload objects. Converts Payload to JSON using Protocol
   * Buffers JSON format.
   */
  public static class PayloadSerializer extends JsonSerializer<Payload> {
    private final JsonFormat.Printer printer =
        JsonFormat.printer().includingDefaultValueFields().preservingProtoFieldNames();

    @Override
    public void serialize(Payload payload, JsonGenerator gen, SerializerProvider serializers)
        throws IOException {
      try {
        String json = printer.print(payload);
        gen.writeRawValue(json);
      } catch (InvalidProtocolBufferException e) {
        throw new IOException("Failed to serialize Payload to JSON", e);
      }
    }
  }

  /**
   * Custom Jackson deserializer for Temporal Payload objects. Converts JSON to Payload using
   * Protocol Buffers JSON format.
   */
  public static class PayloadDeserializer extends JsonDeserializer<Payload> {
    private final JsonFormat.Parser parser = JsonFormat.parser().ignoringUnknownFields();

    @Override
    public Payload deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
      try {
        String json = p.readValueAsTree().toString();
        Payload.Builder builder = Payload.newBuilder();
        parser.merge(json, builder);
        return builder.build();
      } catch (InvalidProtocolBufferException e) {
        throw new IOException("Failed to deserialize JSON to Payload", e);
      }
    }
  }
}
