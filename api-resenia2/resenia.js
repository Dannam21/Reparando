const AWS = require("aws-sdk");
const uuid = require("uuid");
const dynamodb = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();
const TABLE_NAME = process.env.TABLE_NAME;

const crearResenia = async (event) => {
    try {
        const body = typeof event.body === "string" ? JSON.parse(event.body) : event.body;
        const { tenant_id, producto_id, usuario_id, puntaje, comentario, token } = body;

        // Validar que los datos necesarios estén presentes
        if (!tenant_id || !producto_id || !usuario_id || !puntaje || !comentario || !token) {
            return {
                statusCode: 400,
                body: JSON.stringify({ message: "Datos incompletos" }),
            };
        }

        // Invocar la función de validación del token
        const validateTokenResponse = await lambda.invoke({
            FunctionName: "ValidarTokenAcceso", // Nombre de tu función Lambda de validación de tokens
            Payload: JSON.stringify({
                token,
                tenant_id,
                user_id: usuario_id,
            }),
        }).promise();

        const validationResult = JSON.parse(validateTokenResponse.Payload);

        // Revisar si el token es válido
        if (validationResult.statusCode !== 200) {
            return {
                statusCode: validationResult.statusCode,
                body: validationResult.body, // Mensaje de error desde la función de validación
            };
        }

        // Si el token es válido, proceder a crear la reseña
        const resenia_id = uuid.v4();
        const fecha = new Date().toISOString();
        const datos = 1;

        const resenia = {
            "tenant_id#producto_id": `${tenant_id}#${producto_id}`,
            resenia_id,
            fecha,
            usuario_id,
            detalle: {
                puntaje,
                comentario,
            },
            datos,
        };

        const params = {
            TableName: TABLE_NAME,
            Item: resenia,
        };

        await dynamodb.put(params).promise();

        // Devuelve el objeto dentro de "resenia" en el formato deseado
        return {
            statusCode: 200,
            body: JSON.stringify({
                resenia: {
                    "tenant_id#producto_id": resenia["tenant_id#producto_id"],
                    resenia_id: resenia.resenia_id,
                    fecha: resenia.fecha,
                    usuario_id: resenia.usuario_id,
                    detalle: resenia.detalle,
                },
            }),
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: "Error al crear la reseña", error: error.message }),
        };
    }
};

module.exports.crearResenia = crearResenia;
