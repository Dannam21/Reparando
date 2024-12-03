const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    const usuario_id = event.pathParameters?.usuario_id;

    // Verifica que `usuario_id` esté presente
    if (!usuario_id) {
        return {
            statusCode: 400,
            body: JSON.stringify({
                error: "usuario_id es requerido en el path",
            }),
        };
    }

    const params = {
        TableName: process.env.PEDIDOS_TABLE,
        IndexName: "UsuarioIndex", // Debes asegurarte de tener un índice global secundario (GSI) para `usuario_id`
        KeyConditionExpression: "usuario_id = :usuario_id",
        ExpressionAttributeValues: {
            ":usuario_id": usuario_id,
        },
    };

    try {
        const result = await dynamoDB.query(params).promise();
        return {
            statusCode: 200,
            body: JSON.stringify({
                pedidos: result.Items,
            }),
        };
    } catch (error) {
        console.error("Error al obtener pedidos:", error);
        return {
            statusCode: 500,
            body: JSON.stringify({
                error: "Error al obtener pedidos",
                details: error.message,
            }),
        };
    }
};
