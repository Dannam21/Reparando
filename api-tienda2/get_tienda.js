const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    const { tenant_id } = event.pathParameters;  // Obtener el tenant_id de los parámetros de la ruta

    const params = {
        TableName: process.env.TIENDA_TABLE,  // Nombre de la tabla de DynamoDB
        Key: {
            tenant_id,  // Clave primaria de la tabla
        },
    };

    try {
        const result = await dynamoDB.get(params).promise();

        if (!result.Item) {
            return {
                statusCode: 404,
                body: JSON.stringify({ message: "Tienda no encontrada" }),
            };
        }

        return {
            statusCode: 200,
            body: JSON.stringify(result.Item),
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al obtener la tienda", error }),
        };
    }
};
