const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    try {
        const params = {
            TableName: process.env.TIENDA_TABLE,
        };

        // Obtener todas las tiendas
        const result = await dynamoDB.scan(params).promise();

        // Formatear la respuesta con todos los campos
        const tiendas = result.Items.map((item) => ({
            tenant_id: item.tenant_id,
            datos: item.datos || null, // Incluye datos si existen
            fechaCreacion: item.fechaCreacion,
        }));

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: "Tiendas obtenidas exitosamente",
                tiendas,
            }),
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: "Error al obtener tiendas",
                error: error.message,
            }),
        };
    }
};
