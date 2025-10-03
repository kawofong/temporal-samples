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

package io.temporal.app.domain;

import io.temporal.client.WorkflowClientOptions;
import io.temporal.common.converter.CodecDataConverter;
import io.temporal.common.converter.DefaultDataConverter;
import io.temporal.spring.boot.TemporalOptionsCustomizer;
import java.util.Collections;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

@ComponentScan
@Configuration
public class DomainConfig {
  /**
   * For the full list of customizer options, see
   * https://docs.temporal.io/develop/java/spring-boot-integration#customize-options
   */
  @Bean
  public TemporalOptionsCustomizer<WorkflowClientOptions.Builder> customClientOptions() {
    return new TemporalOptionsCustomizer<WorkflowClientOptions.Builder>() {

      @Override
      public WorkflowClientOptions.Builder customize(WorkflowClientOptions.Builder optionsBuilder) {
        return optionsBuilder.setDataConverter(
            new CodecDataConverter(
                DefaultDataConverter.newDefaultInstance(),
                Collections.singletonList(new CryptCodec()),
                true)); // Setting encodeFailureAttributes to true
      }
    };
  }
}
