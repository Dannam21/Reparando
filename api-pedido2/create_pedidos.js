const AWS = require("aws-sdk");
const crypto = require("crypto");
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
            tenant_id, // Clave primaria esperada por DynamoDB
            usuario_id,
            pedido_id: crypto.randomUUID(), // Generación automática del pedido_id
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
