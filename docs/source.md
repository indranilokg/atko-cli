# Installation from source

0. Verify that you have Python 3.6+ . installed

   ```sh
   $ python --version
   ```

1. Clone this repository

   ```sh
   $ git clone https://github.com/indranilokg/atko-cli
   $ cd akto-cli
   ```

2. Build the project

   ```
   $ make
   ```

3. Move the resulting `bin/akto` executable to somewhere in your PATH

   ```sh
   $ sudo mv ./bin/atko /usr/local/bin/
   ```

4. Run `atko version` to check if it worked.