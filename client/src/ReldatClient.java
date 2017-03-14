import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import reldat.ReldatConnection;

public class ReldatClient
{
	public static void main( String[] args )
	{
		if( args.length != 2 )
			usage();
		
		Pattern hostRegex = Pattern.compile( "^(\\d{1,3}[.]\\d{1,3}[.]\\d{1,3}[.]\\d{1,3}):(\\d{1,5})$" );
		Matcher hostMatch = hostRegex.matcher( args[0] );
		
		if( !hostMatch.matches() )
			usage();

		String ipAddress = hostMatch.group( 1 );
		int port         = Integer.parseInt( hostMatch.group( 2 ) );
		
		if( port > 65535 )
			usage();
		
		int maxReceiveWindowSize = Integer.parseInt( args[1] );

		ReldatConnection reldatConn = new ReldatConnection( maxReceiveWindowSize );
		reldatConn.connect( ipAddress, port );
		commandLoop( reldatConn );
		reldatConn.disconnect();
	}

	public static void usage()
	{
		System.out.println( "Usage: java ReldatClient <host IP address>:<host port> <max receive window size in packets>" );
		System.exit( 0 );
	}
	
	public static void commandLoop( ReldatConnection reldatConn )
	{
		boolean disconnect = false;
		Scanner scanner    = new Scanner( System.in );
		scanner.useDelimiter( "\n" );
		
		while( !disconnect )
		{
			System.out.print( "> " );
			String clientInput = scanner.next();
			
			Pattern commandRegex = Pattern.compile( "(\\w+)\\s*(.+)?" );
			Matcher commandMatch = commandRegex.matcher( clientInput );
			
			if( commandMatch.matches() )
			{
				String command = commandMatch.group( 1 );
				
				switch( command )
				{
					case "disconnect":
						disconnect = true;
						break;
					case "transform":
						String filename = commandMatch.group( 2 );
						
						if( filename == null || filename.isEmpty() )
							System.out.println( "  Usage: transform <file>" );
						else
							transform( reldatConn, filename );
						
						break;
					default:
						System.out.println( "Unrecognized command. Valid commands are:\n    disconnect\n    transform" );
						break;
				}
			}
		}
		
		scanner.close();
	}
	
	public static void transform( ReldatConnection reldatConn, String filename )
	{
		// TODO
	}
}
