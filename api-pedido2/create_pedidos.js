const AWS = require("aws-sdk");
const crypto = require("crypto"); // Asegúrate de importar crypto si no lo has hecho
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    let body;

    // Verifica si `event.body` es una cadena y parsea si es necesario
    try {
        body = typeof event.body === "string" ? JSON.parse(event.body) : event.body;
    } catch (error) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: "Invalid JSON format in request body" }),
        };
    }

    const { tenant_id, usuario_id, datos } = body;

    // Validación de datos requeridos
    if (!tenant_id || !usuario_id || !datos || !datos.productos || !datos.precio) {
        return {
            statusCode: 400,
            body: JSON.stringify({
                error: "Missing required data (tenant_id, usuario_id, datos, productos, precio)",
            }),
        };
    }

    const params = {
        TableName: process.env.PEDIDOS_TABLE,
        Item: {
            tenantID: tenant_id,
            usuarioID: usuario_id,
            pedidoID: crypto.randomUUID(),
            estado: "PENDIENTE",
            datos: {
                productos: datos.productos,
                cantidad: datos.productos.length, // Cambiado de `size()` a `length`
                precio: datos.precio,
            },
            fechaPedido: new Date().toISOString(),
        },
    };

    try {
        // Inserta el pedido en DynamoDB
        await dynamoDB.put(params).promise();
        return {
            statusCode: 201,
            body: JSON.stringify({ message: "Pedido creado" }),
        };
    } catch (error) {
        console.error("Error al crear el pedido:", error);
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: "Error al crear pedido",
                error: error.message,
            }),
        };
    }
};
