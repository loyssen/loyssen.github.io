package Demo;

public class Program {

	public static void main(String[] args) {
		// TODO 自动生成的方法存根
		ComputerFactory cf=new ComputerFactory();
		OfficeComputerBuilder oc=new OfficeComputerBuilder();
		cf.BuildComputer(oc);
		oc.getcomputer().ShowSysInfo();
		
		GameComputerBuilder gc=new GameComputerBuilder();
		cf.BuildComputer(gc);
		gc.getcomputer().ShowSysInfo();

	}

}
