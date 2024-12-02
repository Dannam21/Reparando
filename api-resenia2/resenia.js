const AWS = require("aws-sdk");
const uuid = require("uuid");
const dynamodb = new AWS.DynamoDB.DocumentClient();
const TABLE_NAME = process.env.TABLE_NAME;

const crearResenia = async (event) => {
    try {
        const body = typeof event.body === "string" ? JSON.parse(event.body) : event.body;

        const { tenant_id, producto_id, usuario_id, puntaje, comentario, datos } = body;

        if (!tenant_id || !producto_id || !usuario_id || !puntaje || !comentario || !datos) {
            return {
                statusCode: 400,
                body: JSON.stringify({ message: "Datos incompletos" })
            };
        }

        const resenia_id = uuid.v4();
        const fecha = new Date().toISOString(); // Añadimos la fecha
        const resenia = {
            "tenant_id#producto_id": `${tenant_id}#${producto_id}`,
            resenia_id,
            fecha,
            usuario_id,
            detalle: {
                puntaje,
                comentario
            },
            datos
        };

        const params = {
            TableName: TABLE_NAME,
            Item: resenia
        };

        await dynamodb.put(params).promise();

        // Aquí devolvemos el JSON directamente, no como string serializado
        return {
            statusCode: 200,
            body: {
                message: "Reseña creada exitosamente",
                resenia
            }
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: {
                message: "Error al crear la reseña",
                error: error.message
            }
        };
    }
};

module.exports.crearResenia = crearResenia;
