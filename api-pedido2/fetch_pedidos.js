const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    const { tenant_id, usuario_id, estado, lastEvaluatedKey } = event.queryStringParameters || {};

    if (!tenant_id || !usuario_id || !estado) {
        return {
            statusCode: 400,
            body: JSON.stringify({
                error: 'Missing required data (tenant_id, usuario_id, estado)'
            })
        };
    }

    const tenantID_usuarioID = tenant_id + "#" + usuario_id;

    const params = {
        TableName: process.env.PEDIDO_TABLE,
        IndexName: "UsuarioEstadoIndex",
        KeyConditionExpression: "tenantID_usuarioID = :tenant_id#usuario_id AND estado = :estado",
        ExpressionAttributeValues: {
            ":tenant_id#usuario_id": tenantID_usuarioID,
            ":estado": estado,
        },
        ExclusiveStartKey: lastEvaluatedKey ? JSON.parse(lastEvaluatedKey) : undefined // pagination
    };

    try {
        const data = await dynamoDB.query(params).promise();

        // Include the LastEvaluatedKey if there is more data to fetch
        const response = {
            items: data.Items,
            lastEvaluatedKey: data.LastEvaluatedKey ? JSON.stringify(data.LastEvaluatedKey) : null
        };

        return {
            statusCode: 200,
            body: JSON.stringify(response)
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al consultar pedidos", error })
        };
    }
};
