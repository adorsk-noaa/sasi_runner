import java.io.FileInputStream;
import java.lang.System;
import java.util.Properties;
import java.net.URLDecoder;
import java.io.File;

import org.python.core.Py;
import org.python.core.PyException;
import org.python.core.PyFile;
import org.python.core.PySystemState;
import org.python.util.JLineConsole;
import org.python.util.InteractiveConsole;
import org.python.util.InteractiveInterpreter;


public class Main {
  private static InteractiveConsole newInterpreter(boolean interactiveStdin) {
    if (!interactiveStdin) {
      return new InteractiveConsole();
    }

    String interpClass = PySystemState.registry.getProperty(
        "python.console", "");
    if (interpClass.length() > 0) {
      try {
        return (InteractiveConsole)Class.forName(
            interpClass).newInstance();
      } catch (Throwable t) {
        // fall through
      }
    }
    return new JLineConsole();
  }

  public static void main(String[] args) throws Exception {

    // Get .jar's folder.
    String path = Main.class.getProtectionDomain().getCodeSource().getLocation().getPath();
    String decodedPath = URLDecoder.decode(path, "UTF-8");

    XTrustProvider.install();

    PySystemState.initialize(
        PySystemState.getBaseProperties(), 
        new Properties(), args);

    PySystemState systemState = Py.getSystemState();

    // Decide if stdin is interactive
    boolean interactive = ((PyFile)Py.defaultSystemState.stdin).isatty();
    if (!interactive) {
      systemState.ps1 = systemState.ps2 = Py.EmptyString;
    }

    // Now create an interpreter
    InteractiveConsole interp = newInterpreter(interactive);
    systemState.__setattr__("_jy_interpreter", Py.java2py(interp));

    // Run add ./Lib/site-packages to path, relative to jar and run entrypoint.
    String site_packages_path = new File(new File(decodedPath, "Lib").getPath(), "site-packages").getPath();
    String py_code = "try:\n" + 
      " import site\n" +
      " site.addsitedir('" + site_packages_path + "')\n" +
      " import entrypoint\n" +
      " entrypoint.main()\n" +
      "except SystemExit: pass";
    interp.exec(py_code);
  }
}
