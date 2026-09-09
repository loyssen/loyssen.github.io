package Demo;

public class ComputerFactory {
	public void BuildComputer(Builder cb){
		System.out.println("开始组装部件>>>");	
		cb.setupMainBoard();
		cb.setupCPU();
		cb.setupHardDisk();
		cb.setupMemory();
		cb.setupVideoCard();
		System.out.println(">>>主机组装完成");
	}

}
