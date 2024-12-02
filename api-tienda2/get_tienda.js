const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    // Extraer tenant_id desde path
    const tenant_id = event.pathParameters && event.pathParameters.tenant_id; // Acceder correctamente a tenant_id

    if (!tenant_id) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: "tenant_id es requerido" }), // Retornar mensaje de error si no hay tenant_id
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
                body: JSON.stringify({ message: "Tienda no encontrada" }), // Retornar mensaje si no se encuentra la tienda
            };
        }

        return {
            statusCode: 200,
            body: JSON.stringify({
                message: "Tienda encontrada", // Mensaje de éxito
                tienda: {
                    tenant_id: result.Item.tenant_id,
                    name: result.Item.datos.name,
                    fechaCreacion: result.Item.fechaCreacion,
                }
            }),
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: "Error al obtener la tienda", // Mensaje de error
                error: error.message, // Detalles del error
            }),
        };
    }
};
