package Demo;

public class GameComputerBuilder extends Builder{
	public void setupMainBoard(){
		computer.setMainBoard("游戏电脑主板");
	}
	public void setupCPU(){
		computer.setCPU("游戏电脑处理器");
	}
	public void setupHardDisk(){
		computer.setHardDisk("游戏电脑硬盘");
	}
	public void setupMemory(){
		computer.setMemory("游戏电脑内存");
	}
	public void setupVideoCard(){
		computer.setVideoCard("游戏电脑显卡");
	}

}
