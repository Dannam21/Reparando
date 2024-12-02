const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    const { tenant_id, usuario_id, datos } = JSON.parse(event.body);

    if (!tenant_id || !usuario_id || !datos) {
        return {
            statusCode: 400,
            body: JSON.stringify({
                error: 'Missing required data (tenant_id, usuario_id, datos)'
            })
        };
    }

    const params = {
        TableName: process.env.PEDIDOS_TABLE,
        Item: { tenantID: tenant_id,
                usuarioID: usuario_id,
                pedidoID: crypto.randomUUID(),
                estado: "PENDIENTE",
                datos: {
                    productos: datos.productos,
                    cantidad: datos.productos.size(),
                    precio: datos.precio
                },
                fechaPedido: new Date().toISOString() },
    };

    try {
        await dynamoDB.put(params).promise();
        return { statusCode: 201, body: JSON.stringify({ message: "Pedido creado" }) };
    } catch (error) {
        return { statusCode: 500, body: JSON.stringify({ message: "Error al crear pedido", error }) };
    }
};
