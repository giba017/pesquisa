# Use a imagem oficial do Nginx como base
FROM nginx:latest

# Remove o arquivo de configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia o arquivo de configuração personalizado
COPY default.conf /etc/nginx/conf.d/

# Expõe a porta 80 para o mundo externo
EXPOSE 80
EXPOSE 443

# Define o comando para iniciar o Nginx em primeiro plano
#CMD ["nginx", "-g", "daemon off;"]