const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    const { tenant_id, tiendaID } = event.queryStringParameters || {};

    // Validar los parámetros necesarios
    if (!tenant_id || !tiendaID) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: "Faltan parámetros: tenant_id y tiendaID son necesarios" })
        };
    }

    const params = {
        TableName: process.env.TIENDA_TABLE,  // Usar variable de entorno para el nombre de la tabla
        KeyConditionExpression: "tenant_id = :tenant_id AND tiendaID = :tiendaID",
        ExpressionAttributeValues: {
            ":tenant_id": tenant_id,
            ":tiendaID": tiendaID,
        },
    };

    try {
        const data = await dynamoDB.query(params).promise();
        return { statusCode: 200, body: JSON.stringify(data.Items) };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al consultar tienda", error })
        };
    }
};
