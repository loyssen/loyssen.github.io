package Demo;

public class OfficeComputerBuilder extends Builder {
	public void setupMainBoard(){
		computer.setMainBoard("办公电脑主板");
	}
	public void setupCPU(){
		computer.setCPU("办公电脑处理器");
	}
	public void setupHardDisk(){
		computer.setHardDisk("办公电脑硬盘");
	}
	public void setupMemory(){
		computer.setMemory("办公电脑内存");
	}
	public void setupVideoCard(){
		computer.setVideoCard("办公电脑显卡");
	}

}
