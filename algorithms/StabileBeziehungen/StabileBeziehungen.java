import java.util.Vector;
import java.util.Hashtable;
import java.util.Arrays;
import java.awt.Dimension;

/*
Der Algorithmus im Pseudocode:
--------------------------------------------------------------------------------
1. Initialisiere Priorit�tstabellen. 0 ist h�chste Zuneigung.
2. Berechne alle m�glichen stabilen Paare, sortiert nach M�nnern
   Bedingung f�r ein stabiles Paar ist, dass mindestens eine
   Priorit�t null ist.
3. Initialisiere alle Frauen mit "frei".
4. Setze Mann auf 0.
5. Rekursion:
   Falls Mann >= Dimension, return erfolgreich.
   Andernfalls w�hle das erste stabile Paar f�r diesen Mann (existiert immer).
6. Falls die entsprechende Frau frei, markiere sie als unfrei und setze
   Mann = Mann + 1. Rufe die Rekursion erneut auf.
7. Beim R�ckkehr der Rekursion pr�fe, ob der Aufruf erfolgreich war.
   Falls ja, h�nge das aktuelle Paar an die R�ckgabe an und return erfolgreich.
   Falls nein, markiere die aktuelle Frau als unfrei.
8. Pr�fe, ob es noch ein weiteres stabiles Paar f�r diesen Mann gibt.
   Falls mindestens ein Paar vorhanden, w�hle das n�chste und mache weiter mit 6.
   Falls nicht vorhanden, return nicht erfolgreich.
9. Ausgabe R�ckgabeString mit m�glichen Paaren oder Nachricht: "nicht erfolgreich".


Anmerkung: Der Algorithmus l�sst sich noch optimieren, indem man die M�nner nach
Anzahl ihrer stabilen Bindungsm�glichkeiten sortiert. Beim Rekursiven Aufruf nimmt
man die M�nner mit wenigen Bindungsm�glichkeiten als erste, die mit vielen als letzte.

*/

public class StabileBeziehungen {

        private int dimension; // Anzahl Frauen und Anzahl M�nner
	private int[][] frauen; // Priorit�tstabelle. 0 = h�chste Zuneigung.
	private int[][] maenner; // Priorit�tstabelle. 0 = h�chste Zuneigung.
	private int[][] partners; // m�gliche stabile Partner, vom Mann aus gesehen;
	private boolean[] freieFrauen; // f�r rekursion: Frauen, die noch zu haben sind.

	// Konstruktor
	public StabileBeziehungen (int dimension) {
	  	this.dimension = dimension;
	}

	// Initialisierung des Objektes
	public void init() {
	  this.frauen = initGraph(this.dimension);
	  this.maenner = initGraph(this.dimension);
	  this.computePartners();
	  this.freieFrauen = new boolean[this.dimension];
	}

	// initialisiert einen Graphen mit Zufallswerten von 0 <= i < dimension.
	private static int[][] initGraph(int dimension) {

		// initialisiere Graphen.
		Vector values = new Vector();
		int[][] retour = new int[dimension][dimension];
		for (int i=0; i<dimension; ++i) {

			// initialisiere Vector mit Werten
			for (int j=0; j<dimension; ++j) {
				values.add(new Integer(j));
			}

			// nehme zuf�llig nach und nach einen Wert aus dem Vector
			for (int j=0; j<dimension; ++j) {
				int location = (int) Math.floor(Math.random() * values.size());
				retour[i][j] = ((Integer) values.get(location)).intValue();
				values.removeElementAt(location);
			}
		}
		return retour;
	}

	// gibt zur�ck, ob eine Beziehung stabil ist
	// notwendige und hinreichende VBedingung f�r eine stabile Beziehung ist,
	// dass einer der beiden Partner den anderen mit h�chster Priorit�t (0) liebt.
	private boolean istStabil(int mann, int frau) {
	  return this.maenner[mann][frau] * this.frauen[frau][mann] == 0;
	}

	// Kopf der rekursiven Berechnung von stabilen Paaren
	private Dimension[] getPairs() {
	  Arrays.fill(this.freieFrauen, true);
	  Vector result = this.recursePairs(0);

	  // kein Ergebnis gefunden -- gebe null zur�ck
	  if (result == null)
	     return null;

	  // falls Ergebnis, konvertiere Vector in Array.
	  Dimension[] retour = new Dimension[this.dimension];
	  for (int i=0; i<result.size(); ++i) {
	      retour[i] = (Dimension) result.get(i);
	  }
	  return retour;
	}

	// rekursive Berechnung von stabilen Paaren
	private Vector recursePairs(int mann) {

	  // pr�fe, ob Alle Paare gefunden
	  if (mann == this.dimension)
	     return new Vector();

	  // andernfalls bilde m�gliche Paare mit diesem Mann und gehe zum n�chsten
	  for (int i=0; this.partners[mann][i] >= 0; ++i) {
	    if (this.freieFrauen[this.partners[mann][i]]) {
	      this.freieFrauen[this.partners[mann][i]] = false;
	      Vector v = this.recursePairs(mann+1);

	      // falls ein positives Ergebnis aus diesem Zweig resultierte,
	      // f�ge aktuelles Paar an und returniere.
	      if (v != null) {
		v.addElement(new Dimension(mann, this.partners[mann][i]));
		return v;
	      }
	      this.freieFrauen[this.partners[mann][i]] = true;
	    }
	  }
	  // falls kein Ergebnis aus diesem Zwei, return null;
	  return null;
	}

	// berechnet alle m�glichen stabilen Partner sortiert nach M�nnern
	private void computePartners() {
	  this.partners = new int[this.dimension][this.dimension];
	  for (int i=0; i<this.dimension; ++i) {
	    int counter = 0;

	    // suche nach stabilen Paaren und �bernehme ins Array
	    for (int j=0; j<this.dimension; ++j) {
	      if (istStabil(i, j))
	        this.partners[i][counter++] = j;
	    }

	    // f�lle Array mit Negativeintr�gen
	    for (int j=counter; j<this.dimension; ++j) {
	      this.partners[i][j] = -1;
	    }
	  }
	}

	// Ausgabefunktion f�r die Tabellen
	private static String graphToString(int[][] graph) {
		String retour = "";
		for (int i=0; i<graph.length; ++i) {
			for (int j=0; j<graph.length; ++j) {
				retour = retour + graph[i][j] + "\t";
			}
			retour += "\n";
		}
		return retour;
	}

	// ausgabe gefundene paare
	private static String PairsToString(Dimension[] pairs) {
	  String s = "";
	  for (int i=0; i<pairs.length; ++i) {
	    s = s + "(" + pairs[i].width + ", " + pairs[i].height + "); ";
	  }
	  return s;
	}

	public static void main(String args[]) {

	        // falls dimension nicht angegeben, gib Nachricht und beende das Programm.
                if (args.length != 1) {
                  System.out.println("usage: java StabileBeziehungen <dimension>");
                  System.exit(0);
                }

		int dimension = Integer.parseInt(args[0]);

		// lege neue Instanz von StabileBeziehungen an.
		StabileBeziehungen st = new StabileBeziehungen (dimension);
		st.init();

		// Ausgabe der beiden Affinit�tstabellen
		System.out.println("Maenner: ");
		System.out.println(graphToString(st.maenner));
		System.out.println("Frauen: ");
		System.out.println(graphToString(st.frauen));

		// Berechnung und Ausgabe der stabilen Paare
		Dimension[] d = st.getPairs();
		if (d == null) {
		  System.out.println("leider keine Stabilen Beziehungen gefunden.");
		}
		else {
		  System.out.println("Stabile Beziehungen: " + PairsToString(d));
		}
	}

}