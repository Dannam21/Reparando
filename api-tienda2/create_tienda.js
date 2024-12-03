const AWS = require("aws-sdk");
const dynamoDB = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    let body;

    // Parse the incoming body
    if (typeof event.body === "string") {
        body = JSON.parse(event.body);
    } else {
        body = event.body;
    }

    const { tenant_id, datos } = body;

    const params = {
        TableName: process.env.TIENDA_TABLE, // Use environment variable for the table name
        Item: {
            tenant_id,
            datos,
            fechaCreacion: new Date().toISOString(),
        },
    };

    try {
        // Save the item to DynamoDB
        await dynamoDB.put(params).promise();

        // Construct the success response with formatted JSON
        return {
            statusCode: 201,
            body: JSON.stringify(
                {
                    message: "Tienda creada exitosamente",
                    tienda: {
                        tenant_id,
                        datos,
                        fechaCreacion: params.Item.fechaCreacion,
                    },
                },
                null,
                2 // Indent JSON by 2 spaces
            ),
        };
    } catch (error) {
        // Construct the error response
        return {
            statusCode: 500,
            body: JSON.stringify(
                {
                    message: "Error al crear tienda",
                    error: error.message,
                },
                null,
                2 // Indent JSON by 2 spaces
            ),
        };
    }
};
