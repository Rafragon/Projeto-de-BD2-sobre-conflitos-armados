Conflitos Bélicos - Bancos de Dados 2 - 06/2025


Artur Daichi Gonçalves Inazaki - 14676716
Eduardo Veiga - 13633932
Pedro Henrique Chaves Lopo - 14835007
Rafael de Sousa Muniz - 14659644


Requisitos:


* Sistema operacional: Windows ou Linux ou macOS
* Python 3.8 ou superior:
   * Verifique se o Python está instalado: 
No terminal:


python –version


ou


python3 – version


* Banco de dados: PostgreSQL instalado
* Bibliotecas Python (Inseridas dentro do arquivo requirements.txt)




Configurações do Banco de Dados:


Crie o Banco de Dados no PostgreSQL, utilizando o script contido no arquivo SQL_BD2.pdf, Triggers_BD2.pdf e Populacao_BD2.pdf.
No arquivo main.py, ajuste as configurações de conexão com o PostgreSQL:


        self.db_config = {
            'host': 'localhost',
           'database': 'conflitos_bd',  # Nome que você criou
           'user': 'postgres',          # Seu usuário do PostgreSQL
           'password': 'SUA_SENHA_AQUI' # Sua senha do PostgreSQL
}




Já com o banco criado e populado, no terminal:


Acesse a pasta com os arquivos do projeto: 


cd caminho/da/pasta


Crie um ambiente virtual:


        python -m venv venv


Ative o ambiente virtual criado:
No Windows:


        venv\Scripts\activate


No Linux/macOS:


        source venv/bin/activate


Instale as dependências (bibliotecas python):


        pip install -r requirements.txt




Execute a aplicação:


Execute o comando:


        python main.py ou python3 main.py


Em seguida, a janela com a interface gráfica será aberta.


Dentro da interface, vá para a “Conexão DB” e veja se os dados colocados sobre o Banco de Dados estão corretos e depois clique em “Testar Conexão”, se aparecer em baixo “Status: Conectado com sucesso!” poderá prosseguir e acessar as outras abas, se não reajuste os dados de conexão e tente novamente.