// Erro de domínio: o serviço lança com o status sugerido e o handler central
// traduz para a resposta. A mensagem vai ao cliente como texto, como no original.
class DomainError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.name = 'DomainError';
        this.status = status;
    }
}

module.exports = { DomainError };
