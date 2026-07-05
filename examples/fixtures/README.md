# OpsPulse Fixtures

Demonstration assets for pipeline skeleton runs **without** a full `sample-backend/` Java project (D11).

## `app.jar` placeholder

OpsPulse MVP does not ship a runnable Spring Boot application. For local-runner smoke tests, use one of:

1. **Skip build (recommended for Phase 1–2 demo)**

   ```bash
   export SKIP_BUILD=1
   export ARTIFACT_PATH=examples/fixtures/app.jar
   ./local-runner/run-pipeline.sh pr-validation --issue-file examples/issues/001-order-service-feature.md
   ```

2. **Generate a minimal jar** (optional, requires JDK 8+)

   ```bash
   mkdir -p /tmp/opspulse-fixture/src
   echo 'public class Main { public static void main(String[] a) {} }' > /tmp/opspulse-fixture/src/Main.java
   javac /tmp/opspulse-fixture/src/Main.java
   echo 'Main-Class: Main' > /tmp/opspulse-fixture/MANIFEST.MF
   jar cfm examples/fixtures/app.jar /tmp/opspulse-fixture/MANIFEST.MF -C /tmp/opspulse-fixture/src Main.class
   ```

3. **Use your microservice artifact**

   Point `ARTIFACT_PATH` at a jar built from your own JDK 8 microservice repository.

## Directory layout

```
examples/fixtures/
├── app.jar                    # optional placeholder (gitignored except explicit allow)
├── deploy/order-service/
│   └── Dockerfile             # FROM jdk_base_image + COPY app.jar
└── README.md
```

## Docker build example

```bash
export JDK_BASE_IMAGE=eclipse-temurin:8-jre
docker build \
  --build-arg JDK_BASE_IMAGE="${JDK_BASE_IMAGE}" \
  -f examples/fixtures/deploy/order-service/Dockerfile \
  -t order-service:demo \
  examples/fixtures
```

Copy `app.jar` into `examples/fixtures/` before building, or adjust the Dockerfile `COPY` path.
