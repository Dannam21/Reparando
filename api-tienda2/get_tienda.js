const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    console.log("Event received:", JSON.stringify(event, null, 2));  // Para depuración

    // Extraer tenant_id de los parámetros de la ruta
    const tenant_id = event.pathParameters && event.pathParameters.tenant_id;

    print(tenant_id)
    // Validar que tenant_id esté presente
    if (!tenant_id) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: "tenant_id es requerido" }),
        };
    }

    print(tenant_id)
    const params = {
        TableName: process.env.TIENDA_TABLE,
        Key: {
            tenant_id, // Usamos tenant_id para buscar en la tabla
        },
    };

    try {
        const result = await dynamoDB.get(params).promise();

        if (!result.Item) {
            return {
                statusCode: 404
            };
        }

        return {
            statusCode: 200
        };
    } catch (error) {
        return {
            statusCode: 500
        };
    }
};
