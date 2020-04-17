# Database

## DynamoDB

Store data for web crawler and text parsing (e.g., entity patterns). Python interface using boto3.

To create local DynamoDB instance:
- Install Java: https://www.maketecheasier.com/run-java-program-from-command-prompt/
- Follow instructions: https://www.dynamodbguide.com/environment-setup

Navigate to ```dynamo_db``` directory (location may vary), then:

```
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb -port 5000
```

Note: you may need to set the PATH variable to enable java from command line (Windows)

## Neo4j

Store concept graph. Python interface using py2neo.

```
graph = Graph('bolt://localhost:7687', password='pswd')
```

https://medium.com/neo4j/neo4j-get-off-the-ground-in-30min-or-less-3a226a0d48b1

https://neo4j.com/blog/building-python-web-application-using-flask-neo4j/
http://nicolewhite.github.io/neo4j-flask/pages/the-data-model.html
