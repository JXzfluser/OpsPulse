# Layer 3 service image — order-service
# Copy this pattern into your microservice repo: deploy/<service>/Dockerfile

ARG JDK_BASE_IMAGE=eclipse-temurin:8-jre
FROM ${JDK_BASE_IMAGE}

WORKDIR /app
COPY app.jar /app/app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
