// Erro de negócio com o status HTTP sugerido; o middleware de erro faz a tradução.
class DomainError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.name = 'DomainError';
        this.status = status;
    }
}

module.exports = { DomainError };
