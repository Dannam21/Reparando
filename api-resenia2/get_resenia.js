const AWS = require("aws-sdk");
const dynamodb = new AWS.DynamoDB.DocumentClient();
const TABLE_NAME = process.env.TABLE_NAME;

const getResenia = async (event) => {
    try {
        // Parsear parámetros de la solicitud
        const { tenant_id, producto_id } = event.queryStringParameters;

        // Validar parámetros
        if (!tenant_id || !producto_id) {
            return {
                statusCode: 400,
                body: JSON.stringify({ message: "Faltan parámetros: tenant_id y producto_id son requeridos." }),
            };
        }

        // Construir parámetros de consulta
        const params = {
            TableName: TABLE_NAME,
            IndexName: "ProductoIndex", // Usamos el índice secundario local configurado
            KeyConditionExpression: "tenant_id = :tenant_id AND producto_id = :producto_id",
            ExpressionAttributeValues: {
                ":tenant_id": tenant_id,
                ":producto_id": producto_id,
            },
        };

        // Ejecutar consulta
        const result = await dynamodb.query(params).promise();

        // Validar si se encontraron resultados
        if (result.Items.length === 0) {
            return {
                statusCode: 404,
                body: JSON.stringify({ message: "No se encontraron reseñas para los parámetros especificados." }),
            };
        }

        // Retornar las reseñas encontradas
        return {
            statusCode: 200,
            body: JSON.stringify({ resenias: result.Items }),
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al obtener las reseñas", error: error.message }),
        };
    }
};

module.exports.getResenia = getResenia;
