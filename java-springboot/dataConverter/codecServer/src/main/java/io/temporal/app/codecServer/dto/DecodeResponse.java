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

package io.temporal.app.codecServer.dto;

import io.temporal.api.common.v1.Payload;
import java.util.List;

/** Response DTO for decoding payloads. */
public class DecodeResponse {

  private List<Payload> payloads;
  private String error;

  public DecodeResponse() {}

  public DecodeResponse(List<Payload> payloads) {
    this.payloads = payloads;
  }

  public DecodeResponse(String error) {
    this.error = error;
  }

  public List<Payload> getPayloads() {
    return payloads;
  }

  public void setPayloads(List<Payload> payloads) {
    this.payloads = payloads;
  }

  public String getError() {
    return error;
  }

  public void setError(String error) {
    this.error = error;
  }
}
