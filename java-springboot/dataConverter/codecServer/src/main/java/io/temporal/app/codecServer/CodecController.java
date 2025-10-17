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

import io.temporal.api.common.v1.Payload;
import io.temporal.app.codecServer.dto.DecodeRequest;
import io.temporal.app.codecServer.dto.DecodeResponse;
import io.temporal.app.codecServer.dto.EncodeRequest;
import io.temporal.app.codecServer.dto.EncodeResponse;
import io.temporal.app.codecServer.dto.HealthResponse;
import io.temporal.app.domain.CryptCodec;
import io.temporal.payload.codec.PayloadCodecException;
import jakarta.validation.Valid;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller that provides HTTP endpoints for encoding and decoding Temporal payloads using
 * the CryptCodec for encryption/decryption operations.
 */
@RestController
@RequestMapping("/")
@CrossOrigin(
    origins = "*",
    methods = {RequestMethod.POST, RequestMethod.OPTIONS},
    allowedHeaders = "*")
public class CodecController {

  private static final Logger logger = LoggerFactory.getLogger(CodecController.class);
  private final CryptCodec cryptCodec;

  public CodecController(CryptCodec cryptCodec) {
    this.cryptCodec = cryptCodec;
  }

  /**
   * Encodes a list of payloads using the CryptCodec.
   *
   * @param request The encode request containing payloads to encode
   * @return ResponseEntity containing the encoded payloads or error response
   */
  @PostMapping(
      value = "/encode",
      consumes = MediaType.APPLICATION_JSON_VALUE,
      produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<EncodeResponse> encode(@Valid @RequestBody EncodeRequest request) {
    try {
      logger.debug("Encoding {} payloads", request.getPayloads().size());

      List<Payload> encodedPayloads = cryptCodec.encode(request.getPayloads());

      EncodeResponse response = new EncodeResponse(encodedPayloads);
      logger.debug("Successfully encoded {} payloads", encodedPayloads.size());

      return ResponseEntity.ok(response);

    } catch (PayloadCodecException e) {
      logger.error("Failed to encode payloads", e);
      return ResponseEntity.status(HttpStatus.BAD_REQUEST)
          .body(new EncodeResponse("Encoding failed: " + e.getMessage()));
    } catch (Exception e) {
      logger.error("Unexpected error during encoding", e);
      return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
          .body(new EncodeResponse("Internal server error during encoding"));
    }
  }

  /**
   * Decodes a list of payloads using the CryptCodec.
   *
   * @param request The decode request containing payloads to decode
   * @return ResponseEntity containing the decoded payloads or error response
   */
  @PostMapping(
      value = "/decode",
      consumes = MediaType.APPLICATION_JSON_VALUE,
      produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<DecodeResponse> decode(@Valid @RequestBody DecodeRequest request) {
    try {
      logger.debug("Decoding {} payloads", request.getPayloads().size());

      List<Payload> decodedPayloads = cryptCodec.decode(request.getPayloads());

      DecodeResponse response = new DecodeResponse(decodedPayloads);
      logger.debug("Successfully decoded {} payloads", decodedPayloads.size());

      return ResponseEntity.ok(response);

    } catch (PayloadCodecException e) {
      logger.error("Failed to decode payloads", e);
      return ResponseEntity.status(HttpStatus.BAD_REQUEST)
          .body(new DecodeResponse("Decoding failed: " + e.getMessage()));
    } catch (Exception e) {
      logger.error("Unexpected error during decoding", e);
      return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
          .body(new DecodeResponse("Internal server error during decoding"));
    }
  }

  /**
   * Health check endpoint to verify the codec server is running.
   *
   * @return Simple health status response
   */
  @GetMapping(value = "/health", produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<HealthResponse> health() {
    return ResponseEntity.ok(new HealthResponse("OK", "Codec server is running"));
  }
}
