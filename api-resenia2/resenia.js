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
        const fecha = new Date().toISOString(); // Fecha actual en formato ISO
        const resenia = {
            "tenant_id#producto_id": `${tenant_id}#${producto_id}`, // Clave de partición combinada
            resenia_id, // Clave de ordenamiento principal
            fecha, // Clave de ordenamiento secundaria
            usuario_id,
            detalle: {
                puntaje,
                comentario
            },
            datos // Nuevo campo
        };

        const params = {
            TableName: TABLE_NAME,
            Item: resenia
        };

        await dynamodb.put(params).promise();

        return {
            statusCode: 200,
            body: JSON.stringify({ message: "Reseña creada exitosamente", resenia })
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al crear la reseña", error: error.message })
        };
    }
};

module.exports.crearResenia = crearResenia;
