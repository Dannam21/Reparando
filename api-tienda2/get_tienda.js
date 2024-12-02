const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    // Extraer tenant_id desde path
    const tenant_id = event.pathParameters ? event.pathParameters.tenant_id : null;  // Acceder a tenant_id desde pathParameters

    if (!tenant_id) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: "tenant_id es requerido" }),
        };
    }

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
                statusCode: 404,
                body: JSON.stringify({ message: "Tienda no encontrada" }),
            };
        }

        // Aquí se crea la respuesta de manera legible
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: "Tienda encontrada",
                tienda: {
                    tenant_id: result.Item.tenant_id,
                    name: result.Item.datos.name,
                    fechaCreacion: result.Item.fechaCreacion
                }
            }, null, 2),  // null, 2 le da un formato más legible (con sangrías)
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: "Error al obtener la tienda",
                error: error.message,
            }),
        };
    }
};
