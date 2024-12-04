const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async () => {
    try {
        const params = {
            TableName: process.env.TIENDA_TABLE,
        };

        const result = await dynamoDB.scan(params).promise();

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",  // Permitir cualquier origen
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
            },
            body: JSON.stringify({
                message: "Tiendas obtenidas exitosamente",
                tiendas: result.Items.map((tienda) => ({
                    tenant_id: tienda.tenant_id,
                    datos: tienda.datos,
                    fechaCreacion: tienda.fechaCreacion,
                })),
            }),
        };
    } catch (error) {
        return {
            statusCode: 500,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",  // Permitir cualquier origen
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
            },
            body: JSON.stringify({
                message: "Error al obtener las tiendas",
                error: error.message,
            }),
        };
    }
};
