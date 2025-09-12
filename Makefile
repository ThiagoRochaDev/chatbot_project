.PHONY: grafana prometheus loki tempo otel-collector all

NAMESPACE ?= chatbot-monitoring

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker exec -it rag_chatbot bash





grafana:
	minikube service grafana --url -n $(NAMESPACE)

prometheus:
	minikube service prometheus --url -n $(NAMESPACE)

loki:
	minikube service loki --url -n $(NAMESPACE)

tempo:
	minikube service tempo --url -n $(NAMESPACE)

otel-collector:
	minikube service otel-collector --url -n $(NAMESPACE)

# all:
#     minikube service grafana prometheus loki tempo otel-collector --url -n chatbot-monitoring